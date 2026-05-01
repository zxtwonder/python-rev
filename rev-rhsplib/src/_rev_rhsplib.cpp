/*
 * _rev_rhsplib.cpp
 *
 * pybind11 bindings for librhsp — the REV Hub Serial Protocol C library.
 *
 * All methods on PyRevHub are synchronous (blocking).  The Python layer in
 * rev_rhsplib/__init__.py wraps them with asyncio.run_in_executor so that they
 * do not block the event loop.  The GIL is released around every blocking C
 * call so that other Python threads remain responsive during serial I/O.
 */

#include <cstdint>
#include <cstring>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/native_enum.h>
#include <pybind11/stl.h>

// librhsp public headers
#include "rhsp/rhsp.h"
#include "rhsp/revhub.h"
#include "rhsp/serial.h"
#include "rhsp/deviceControl.h"
#include "rhsp/motor.h"
#include "rhsp/servo.h"
#include "rhsp/dio.h"
#include "rhsp/i2c.h"
#include "rhsp/module.h"
#include "rhsp/errors.h"

// Internal header needed for sendReadCommand / sendWriteCommand
#include "internal/command.h"
#include "internal/packet.h"

namespace py = pybind11;

// ── Error code enums ──────────────────────────────────────────────────────────

enum class RhspLibErrorCode : int {
    GENERAL_ERROR          = RHSP_ERROR,
    TIMEOUT                = RHSP_ERROR_RESPONSE_TIMEOUT,
    MSG_NUMBER_MISMATCH    = RHSP_ERROR_MSG_NUMBER_MISMATCH,
    NACK                   = RHSP_ERROR_NACK_RECEIVED,
    SERIAL_ERROR           = RHSP_ERROR_SERIALPORT,
    NOT_OPENED             = RHSP_ERROR_NOT_OPENED,
    COMMAND_NOT_SUPPORTED  = RHSP_ERROR_COMMAND_NOT_SUPPORTED,
    UNEXPECTED_RESPONSE    = RHSP_ERROR_UNEXPECTED_RESPONSE,
    NO_HUBS_DISCOVERED     = RHSP_ERROR_NO_HUBS_DISCOVERED,
    ARG_OUT_OF_RANGE_START = RHSP_ERROR_ARG_0_OUT_OF_RANGE,
    ARG_OUT_OF_RANGE_END   = RHSP_ERROR_ARG_5_OUT_OF_RANGE,
};

enum class SerialErrorCode : int {
    GENERAL_ERROR       = RHSP_SERIAL_ERROR,
    UNABLE_TO_OPEN      = RHSP_SERIAL_ERROR_OPENING,
    INVALID_ARGS        = RHSP_SERIAL_ERROR_ARGS,
    CONFIGURATION_ERROR = RHSP_SERIAL_ERROR_CONFIGURE,
    IO_ERROR            = RHSP_SERIAL_ERROR_IO,
};

// ── Exception ────────────────────────────────────────────────────────────────

/**
 * C++ exception that carries an librhsp error code and an optional NACK code.
 * A registered translator converts this to a Python RhspLibError instance.
 */
struct RhspLibException : public std::exception {
    int error_code;
    bool has_nack;
    uint8_t nack_code;

    explicit RhspLibException(int code)
        : error_code(code), has_nack(false), nack_code(0) {}

    RhspLibException(int code, uint8_t nack)
        : error_code(code), has_nack(true), nack_code(nack) {}

    const char* what() const noexcept override { return "RhspLibNativeError"; }
};

/** Throw RhspLibException if result is negative. */
static void check_result(int result, uint8_t nack_code) {
    if (result < 0) {
        if (result == RHSP_ERROR_NACK_RECEIVED) {
            throw RhspLibException(result, nack_code);
        }
        throw RhspLibException(result);
    }
}

// ── Serial wrapper ────────────────────────────────────────────────────────────

class PySerial {
public:
    PySerial() { rhsp_serialInit(&serial_); }

    ~PySerial() {
        if (opened_) {
            rhsp_serialClose(&serial_);
        }
    }

    void open(const std::string& port, uint32_t baudrate, uint32_t databits,
              RhspSerialParity parity, uint32_t stopbits,
              RhspSerialFlowControl flow_control) {
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_serialOpen(&serial_, port.c_str(), baudrate, databits,
                                     parity, stopbits, flow_control);
        }
        if (result != RHSP_SERIAL_NOERROR) {
            throw RhspLibException(result);
        }
        opened_ = true;
    }

    void close() {
        if (opened_) {
            py::gil_scoped_release release;
            rhsp_serialClose(&serial_);
            opened_ = false;
        }
    }

    std::vector<uint8_t> read(size_t num_bytes) {
        std::vector<uint8_t> buf(num_bytes);
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_serialRead(&serial_, buf.data(), num_bytes);
        }
        if (result < 0) {
            throw RhspLibException(RHSP_SERIAL_ERROR);
        }
        buf.resize(static_cast<size_t>(result));
        return buf;
    }

    void write(const std::vector<uint8_t>& bytes) {
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_serialWrite(&serial_, bytes.data(), bytes.size());
        }
        if (result < 0) {
            throw RhspLibException(RHSP_SERIAL_ERROR);
        }
    }

    RhspSerial* get() { return &serial_; }

private:
    RhspSerial serial_{};
    bool opened_ = false;
};

// ── RevHub wrapper ───────────────────────────────────────────────────────────

class PyRevHub {
public:
    PyRevHub() = default;

    ~PyRevHub() {
        if (hub_) {
            rhsp_close(hub_);
            freeRevHub(hub_);
        }
    }

    void open(PySerial& serial, uint8_t dest_address) {
        if (hub_) {
            rhsp_close(hub_);
            freeRevHub(hub_);
        }
        py::gil_scoped_release release;
        hub_ = rhsp_allocRevHub(serial.get(), dest_address);
    }

    bool is_opened() const {
        return hub_ != nullptr && rhsp_isOpened(hub_);
    }

    void close() {
        if (hub_) {
            py::gil_scoped_release release;
            rhsp_close(hub_);
            freeRevHub(hub_);
            hub_ = nullptr;
        }
    }

    void set_dest_address(uint8_t addr) {
        require_open();
        rhsp_setDestinationAddress(hub_, addr);
    }

    uint8_t get_dest_address() const {
        require_open();
        return rhsp_getDestinationAddress(hub_);
    }

    void set_response_timeout_ms(uint32_t ms) {
        require_open();
        rhsp_setResponseTimeoutMs(hub_, ms);
    }

    uint32_t get_response_timeout_ms() const {
        require_open();
        return rhsp_responseTimeoutMs(hub_);
    }

    // ── Custom commands ───────────────────────────────────────────────────

    std::vector<uint8_t> send_write_command(uint16_t packet_type_id,
                                             const std::vector<uint8_t>& payload) {
        require_open();
        RhspPayloadData resp{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_sendWriteCommand(hub_, packet_type_id,
                                           payload.data(),
                                           static_cast<uint16_t>(payload.size()),
                                           &resp, &nack);
        }
        check_result(result, nack);
        return std::vector<uint8_t>(resp.data, resp.data + resp.size);
    }

    std::vector<uint8_t> send_read_command(uint16_t packet_type_id,
                                            const std::vector<uint8_t>& payload) {
        require_open();
        RhspPayloadData resp{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_sendReadCommand(hub_, packet_type_id,
                                          payload.data(),
                                          static_cast<uint16_t>(payload.size()),
                                          &resp, &nack);
        }
        check_result(result, nack);
        return std::vector<uint8_t>(resp.data, resp.data + resp.size);
    }

    // ── Module status / control ───────────────────────────────────────────

    py::dict get_module_status(bool clear_status) {
        require_open();
        RhspModuleStatus status{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getModuleStatus(hub_, clear_status ? 1 : 0, &status, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["status_word"] = status.statusWord;
        d["motor_alerts"] = status.motorAlerts;
        return d;
    }

    void send_keep_alive() {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_sendKeepAlive(hub_, &nack);
        }
        check_result(result, nack);
    }

    void send_fail_safe() {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_sendFailSafe(hub_, &nack);
        }
        check_result(result, nack);
    }

    void set_new_module_address(uint8_t new_addr) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setNewModuleAddress(hub_, new_addr, &nack);
        }
        check_result(result, nack);
    }

    py::dict query_interface(const std::string& name) {
        require_open();
        RhspModuleInterface intf{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_queryInterface(hub_, name.c_str(), &intf, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["name"] = intf.name ? std::string(intf.name) : name;
        d["first_packet_id"] = intf.firstPacketID;
        d["number_id_values"] = intf.numberIDValues;
        return d;
    }

    uint16_t get_interface_packet_id(const std::string& name, uint16_t function_number) {
        require_open();
        uint16_t packet_id = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getInterfacePacketID(hub_, name.c_str(), function_number,
                                               &packet_id, &nack);
        }
        check_result(result, nack);
        return packet_id;
    }

    void set_debug_log_level(int group, int level) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setDebugLogLevel(
                hub_,
                static_cast<RhspDebugGroupNumber>(group),
                static_cast<RhspVerbosityLevel>(level),
                &nack);
        }
        check_result(result, nack);
    }

    // ── LED ──────────────────────────────────────────────────────────────

    void set_module_led_color(uint8_t red, uint8_t green, uint8_t blue) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setModuleLedColor(hub_, red, green, blue, &nack);
        }
        check_result(result, nack);
    }

    py::tuple get_module_led_color() {
        require_open();
        uint8_t r = 0, g = 0, b = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getModuleLedColor(hub_, &r, &g, &b, &nack);
        }
        check_result(result, nack);
        return py::make_tuple(r, g, b);
    }

    void set_module_led_pattern(const std::vector<uint32_t>& steps) {
        require_open();
        if (steps.size() != 16) {
            throw std::invalid_argument("led_pattern must have exactly 16 steps");
        }
        RhspLedPattern pat{};
        pat.rgbtPatternStep0  = steps[0];  pat.rgbtPatternStep1  = steps[1];
        pat.rgbtPatternStep2  = steps[2];  pat.rgbtPatternStep3  = steps[3];
        pat.rgbtPatternStep4  = steps[4];  pat.rgbtPatternStep5  = steps[5];
        pat.rgbtPatternStep6  = steps[6];  pat.rgbtPatternStep7  = steps[7];
        pat.rgbtPatternStep8  = steps[8];  pat.rgbtPatternStep9  = steps[9];
        pat.rgbtPatternStep10 = steps[10]; pat.rgbtPatternStep11 = steps[11];
        pat.rgbtPatternStep12 = steps[12]; pat.rgbtPatternStep13 = steps[13];
        pat.rgbtPatternStep14 = steps[14]; pat.rgbtPatternStep15 = steps[15];
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setModuleLedPattern(hub_, &pat, &nack);
        }
        check_result(result, nack);
    }

    std::vector<uint32_t> get_module_led_pattern() {
        require_open();
        RhspLedPattern pat{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getModuleLedPattern(hub_, &pat, &nack);
        }
        check_result(result, nack);
        return {
            pat.rgbtPatternStep0,  pat.rgbtPatternStep1,
            pat.rgbtPatternStep2,  pat.rgbtPatternStep3,
            pat.rgbtPatternStep4,  pat.rgbtPatternStep5,
            pat.rgbtPatternStep6,  pat.rgbtPatternStep7,
            pat.rgbtPatternStep8,  pat.rgbtPatternStep9,
            pat.rgbtPatternStep10, pat.rgbtPatternStep11,
            pat.rgbtPatternStep12, pat.rgbtPatternStep13,
            pat.rgbtPatternStep14, pat.rgbtPatternStep15,
        };
    }

    // ── Device control ────────────────────────────────────────────────────

    py::dict get_bulk_input_data() {
        require_open();
        RhspBulkInputData data{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getBulkInputData(hub_, &data, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["digital_inputs"]     = data.digitalInputs;
        d["motor0_position_enc"] = data.motor0position_enc;
        d["motor1_position_enc"] = data.motor1position_enc;
        d["motor2_position_enc"] = data.motor2position_enc;
        d["motor3_position_enc"] = data.motor3position_enc;
        d["motor_status"]        = data.motorStatus;
        d["motor0_velocity_cps"] = data.motor0velocity_cps;
        d["motor1_velocity_cps"] = data.motor1velocity_cps;
        d["motor2_velocity_cps"] = data.motor2velocity_cps;
        d["motor3_velocity_cps"] = data.motor3velocity_cps;
        d["analog0_mv"]          = data.analog0_mV;
        d["analog1_mv"]          = data.analog1_mV;
        d["analog2_mv"]          = data.analog2_mV;
        d["analog3_mv"]          = data.analog3_mV;
        return d;
    }

    int16_t get_adc(uint8_t channel, uint8_t raw_mode) {
        require_open();
        int16_t value = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getADC(hub_, channel, raw_mode, &value, &nack);
        }
        check_result(result, nack);
        return value;
    }

    void phone_charge_control(bool enable) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_phoneChargeControl(hub_, enable ? 1 : 0, &nack);
        }
        check_result(result, nack);
    }

    bool phone_charge_query() {
        require_open();
        uint8_t enabled = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_phoneChargeQuery(hub_, &enabled, &nack);
        }
        check_result(result, nack);
        return enabled != 0;
    }

    void inject_data_log_hint(const std::string& hint) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_injectDataLogHint(hub_, hint.c_str(), &nack);
        }
        check_result(result, nack);
    }

    std::string read_version_string() {
        require_open();
        char buf[41] = {};
        uint8_t length = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_readVersionString(hub_, &length, buf, &nack);
        }
        check_result(result, nack);
        buf[length] = '\0';
        return std::string(buf, length);
    }

    py::dict read_version() {
        require_open();
        RhspVersion ver{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_readVersion(hub_, &ver, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["engineering_revision"] = ver.engineeringRevision;
        d["minor_version"]        = ver.minorVersion;
        d["major_version"]        = ver.majorVersion;
        d["minor_hw_revision"]    = ver.minorHwRevision;
        d["major_hw_revision"]    = ver.majorHwRevision;
        d["hw_type"]              = ver.hwType;
        return d;
    }

    void ftdi_reset_control(bool enable) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_ftdiResetControl(hub_, enable ? 1 : 0, &nack);
        }
        check_result(result, nack);
    }

    bool ftdi_reset_query() {
        require_open();
        uint8_t ctrl = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_ftdiResetQuery(hub_, &ctrl, &nack);
        }
        check_result(result, nack);
        return ctrl != 0;
    }

    // ── Digital I/O ──────────────────────────────────────────────────────

    void set_single_digital_output(uint8_t pin, bool value) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setSingleOutput(hub_, pin, value ? 1 : 0, &nack);
        }
        check_result(result, nack);
    }

    void set_all_digital_outputs(uint8_t packed) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setAllOutputs(hub_, packed, &nack);
        }
        check_result(result, nack);
    }

    void set_digital_direction(uint8_t pin, uint8_t direction_output) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setDirection(hub_, pin, direction_output, &nack);
        }
        check_result(result, nack);
    }

    uint8_t get_digital_direction(uint8_t pin) {
        require_open();
        uint8_t dir = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getDirection(hub_, pin, &dir, &nack);
        }
        check_result(result, nack);
        return dir;
    }

    bool get_single_digital_input(uint8_t pin) {
        require_open();
        uint8_t value = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getSingleInput(hub_, pin, &value, &nack);
        }
        check_result(result, nack);
        return value != 0;
    }

    uint8_t get_all_digital_inputs() {
        require_open();
        uint8_t packed = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getAllInputs(hub_, &packed, &nack);
        }
        check_result(result, nack);
        return packed;
    }

    // ── I2C ──────────────────────────────────────────────────────────────

    void configure_i2c_channel(uint8_t channel, uint8_t speed_code) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_configureI2cChannel(hub_, channel, speed_code, &nack);
        }
        check_result(result, nack);
    }

    uint8_t configure_i2c_query(uint8_t channel) {
        require_open();
        uint8_t speed = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_configureI2cQuery(hub_, channel, &speed, &nack);
        }
        check_result(result, nack);
        return speed;
    }

    void write_single_byte(uint8_t channel, uint8_t addr, uint8_t byte) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_writeSingleByte(hub_, channel, addr, byte, &nack);
        }
        check_result(result, nack);
    }

    void write_multiple_bytes(uint8_t channel, uint8_t addr,
                              const std::vector<uint8_t>& bytes) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_writeMultipleBytes(hub_, channel, addr,
                                             static_cast<uint8_t>(bytes.size()),
                                             bytes.data(), &nack);
        }
        check_result(result, nack);
    }

    py::dict write_status_query(uint8_t channel) {
        require_open();
        uint8_t status = 0, written = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_writeStatusQuery(hub_, channel, &status, &written, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["i2c_transaction_status"] = status;
        d["num_bytes_written"]      = written;
        return d;
    }

    void read_single_byte(uint8_t channel, uint8_t addr) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_readSingleByte(hub_, channel, addr, &nack);
        }
        check_result(result, nack);
    }

    void read_multiple_bytes(uint8_t channel, uint8_t addr, uint8_t n) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_readMultipleBytes(hub_, channel, addr, n, &nack);
        }
        check_result(result, nack);
    }

    void write_read_multiple_bytes(uint8_t channel, uint8_t addr,
                                    uint8_t n, uint8_t start_address) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_writeReadMultipleBytes(hub_, channel, addr, n, start_address, &nack);
        }
        check_result(result, nack);
    }

    py::dict read_status_query(uint8_t channel) {
        require_open();
        uint8_t status = 0, bytes_read = 0, nack = 0;
        uint8_t payload[RHSP_I2C_TRANSACTION_ARRAY_MAX_BUFFER_SIZE] = {};
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_readStatusQuery(hub_, channel, &status, &bytes_read,
                                          payload, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["i2c_transaction_status"] = status;
        d["num_bytes_read"]         = bytes_read;
        d["bytes"] = std::vector<uint8_t>(payload, payload + bytes_read);
        return d;
    }

    // ── Motor ─────────────────────────────────────────────────────────────

    void set_motor_channel_mode(uint8_t channel, int mode, bool float_at_zero) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setMotorChannelMode(hub_, channel,
                                              static_cast<MotorMode>(mode),
                                              float_at_zero ? 1 : 0, &nack);
        }
        check_result(result, nack);
    }

    py::dict get_motor_channel_mode(uint8_t channel) {
        require_open();
        uint8_t mode = 0, faz = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getMotorChannelMode(hub_, channel, &mode, &faz, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["motor_mode"]    = static_cast<int>(mode);
        d["float_at_zero"] = faz != 0;
        return d;
    }

    void set_motor_channel_enable(uint8_t channel, bool enable) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setMotorChannelEnable(hub_, channel, enable ? 1 : 0, &nack);
        }
        check_result(result, nack);
    }

    bool get_motor_channel_enable(uint8_t channel) {
        require_open();
        uint8_t enabled = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getMotorChannelEnable(hub_, channel, &enabled, &nack);
        }
        check_result(result, nack);
        return enabled != 0;
    }

    void set_motor_channel_current_alert_level(uint8_t channel, uint16_t limit_ma) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setMotorChannelCurrentAlertLevel(hub_, channel, limit_ma, &nack);
        }
        check_result(result, nack);
    }

    uint16_t get_motor_channel_current_alert_level(uint8_t channel) {
        require_open();
        uint16_t limit = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getMotorChannelCurrentAlertLevel(hub_, channel, &limit, &nack);
        }
        check_result(result, nack);
        return limit;
    }

    void reset_encoder(uint8_t channel) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_resetEncoder(hub_, channel, &nack);
        }
        check_result(result, nack);
    }

    void set_motor_constant_power(uint8_t channel, double power) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setMotorConstantPower(hub_, channel, power, &nack);
        }
        check_result(result, nack);
    }

    double get_motor_constant_power(uint8_t channel) {
        require_open();
        double power = 0.0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getMotorConstantPower(hub_, channel, &power, &nack);
        }
        check_result(result, nack);
        return power;
    }

    void set_motor_target_velocity(uint8_t channel, int16_t velocity_cps) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setMotorTargetVelocity(hub_, channel, velocity_cps, &nack);
        }
        check_result(result, nack);
    }

    int16_t get_motor_target_velocity(uint8_t channel) {
        require_open();
        int16_t vel = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getMotorTargetVelocity(hub_, channel, &vel, &nack);
        }
        check_result(result, nack);
        return vel;
    }

    void set_motor_target_position(uint8_t channel, int32_t position, uint16_t tolerance) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setMotorTargetPosition(hub_, channel, position, tolerance, &nack);
        }
        check_result(result, nack);
    }

    py::dict get_motor_target_position(uint8_t channel) {
        require_open();
        int32_t pos = 0;
        uint16_t tol = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getMotorTargetPosition(hub_, channel, &pos, &tol, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["target_position"]  = pos;
        d["target_tolerance"] = tol;
        return d;
    }

    bool is_motor_at_target(uint8_t channel) {
        require_open();
        uint8_t at = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_isMotorAtTarget(hub_, channel, &at, &nack);
        }
        check_result(result, nack);
        return at != 0;
    }

    int32_t get_encoder_position(uint8_t channel) {
        require_open();
        int32_t pos = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getEncoderPosition(hub_, channel, &pos, &nack);
        }
        check_result(result, nack);
        return pos;
    }

    /**
     * Set closed-loop coefficients.
     *
     * params dict must contain "type" (0=PID, 1=PIDF), "p", "i", "d",
     * and optionally "f" (required for PIDF).
     */
    void set_closed_loop_control_coefficients(uint8_t channel, int mode,
                                               const py::dict& params) {
        require_open();
        ClosedLoopControlParameters p{};
        int type = params["type"].cast<int>();
        p.type = type;
        p.pid.p = params["p"].cast<double>();
        p.pid.i = params["i"].cast<double>();
        p.pid.d = params["d"].cast<double>();
        if (type == PIDF_TAG) {
            p.pidf.f = params["f"].cast<double>();
        }
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setClosedLoopControlCoefficients(
                hub_, channel, static_cast<MotorMode>(mode), &p, &nack);
        }
        check_result(result, nack);
    }

    py::dict get_closed_loop_control_coefficients(uint8_t channel, int mode) {
        require_open();
        ClosedLoopControlParameters p{};
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getClosedLoopControlCoefficients(
                hub_, channel, static_cast<MotorMode>(mode), &p, &nack);
        }
        check_result(result, nack);
        py::dict d;
        d["type"] = p.type;
        d["p"]    = p.pid.p;
        d["i"]    = p.pid.i;
        d["d"]    = p.pid.d;
        if (p.type == PIDF_TAG) {
            d["f"] = p.pidf.f;
        }
        return d;
    }

    // ── Servo ─────────────────────────────────────────────────────────────

    void set_servo_configuration(uint8_t channel, uint16_t frame_period) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setServoConfiguration(hub_, channel, frame_period, &nack);
        }
        check_result(result, nack);
    }

    uint16_t get_servo_configuration(uint8_t channel) {
        require_open();
        uint16_t period = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getServoConfiguration(hub_, channel, &period, &nack);
        }
        check_result(result, nack);
        return period;
    }

    void set_servo_pulse_width(uint8_t channel, uint16_t width) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setServoPulseWidth(hub_, channel, width, &nack);
        }
        check_result(result, nack);
    }

    uint16_t get_servo_pulse_width(uint8_t channel) {
        require_open();
        uint16_t width = 0;
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getServoPulseWidth(hub_, channel, &width, &nack);
        }
        check_result(result, nack);
        return width;
    }

    void set_servo_enable(uint8_t channel, bool enable) {
        require_open();
        uint8_t nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_setServoEnable(hub_, channel, enable ? 1 : 0, &nack);
        }
        check_result(result, nack);
    }

    bool get_servo_enable(uint8_t channel) {
        require_open();
        uint8_t enabled = 0, nack = 0;
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_getServoEnable(hub_, channel, &enabled, &nack);
        }
        check_result(result, nack);
        return enabled != 0;
    }

    // ── Static: discovery ─────────────────────────────────────────────────

    static py::dict discover_rev_hubs(PySerial& serial) {
        RhspDiscoveredAddresses addrs{};
        int result;
        {
            py::gil_scoped_release release;
            result = rhsp_discoverRevHubs(serial.get(), &addrs);
        }
        if (result < 0) {
            throw RhspLibException(result);
        }
        py::dict d;
        d["parent_address"]          = addrs.parentAddress;
        d["number_of_child_modules"] = addrs.numberOfChildModules;
        std::vector<uint8_t> children(addrs.childAddresses,
                                      addrs.childAddresses + addrs.numberOfChildModules);
        d["child_addresses"] = children;
        return d;
    }

private:
    RhspRevHub* hub_ = nullptr;

    void require_open() const {
        if (!hub_ || !rhsp_isOpened(hub_)) {
            throw RhspLibException(RHSP_ERROR_NOT_OPENED);
        }
    }
};

// ── Module definition ─────────────────────────────────────────────────────────

PYBIND11_MODULE(_rev_rhsplib, m) {
    m.doc() = "Low-level pybind11 bindings for librhsp (REV Hub Serial Protocol)";

    // ── Error class ───────────────────────────────────────────────────────
    // Defined first so the translator can reference it.
    static py::exception<RhspLibException> py_rhsp_error(m, "RhspLibNativeError",
                                                          PyExc_RuntimeError);

    py::register_exception_translator([](std::exception_ptr p) {
        try {
            if (p) std::rethrow_exception(p);
        } catch (const RhspLibException& e) {
            PyObject* exc = PyObject_CallOneArg(py_rhsp_error.ptr(),
                                                PyUnicode_FromString(e.what()));
            if (exc) {
                PyObject_SetAttrString(exc, "error_code", PyLong_FromLong(e.error_code));
                PyObject_SetAttrString(exc, "nack_code",
                    e.has_nack ? PyLong_FromLong(e.nack_code) : Py_None);
                PyErr_SetObject(py_rhsp_error.ptr(), exc);
                Py_DECREF(exc);
            }
        }
    });

    // ── Enums ─────────────────────────────────────────────────────────────
    py::native_enum<RhspSerialParity>(m, "SerialParity", "enum.IntEnum")
        .value("None_", RHSP_SERIAL_PARITY_NONE)
        .value("Odd",   RHSP_SERIAL_PARITY_ODD)
        .value("Even",  RHSP_SERIAL_PARITY_EVEN)
        .finalize();

    py::native_enum<RhspSerialFlowControl>(m, "SerialFlowControl", "enum.IntEnum")
        .value("None_",     RHSP_SERIAL_FLOW_CONTROL_NONE)
        .value("Hardware",  RHSP_SERIAL_FLOW_CONTROL_HARDWARE)
        .value("Software",  RHSP_SERIAL_FLOW_CONTROL_SOFTWARE)
        .finalize();

    py::native_enum<RhspLibErrorCode>(m, "RhspLibErrorCode", "enum.IntEnum")
        .value("GENERAL_ERROR",          RhspLibErrorCode::GENERAL_ERROR)
        .value("TIMEOUT",                RhspLibErrorCode::TIMEOUT)
        .value("MSG_NUMBER_MISMATCH",    RhspLibErrorCode::MSG_NUMBER_MISMATCH)
        .value("NACK",                   RhspLibErrorCode::NACK)
        .value("SERIAL_ERROR",           RhspLibErrorCode::SERIAL_ERROR)
        .value("NOT_OPENED",             RhspLibErrorCode::NOT_OPENED)
        .value("COMMAND_NOT_SUPPORTED",  RhspLibErrorCode::COMMAND_NOT_SUPPORTED)
        .value("UNEXPECTED_RESPONSE",    RhspLibErrorCode::UNEXPECTED_RESPONSE)
        .value("NO_HUBS_DISCOVERED",     RhspLibErrorCode::NO_HUBS_DISCOVERED)
        .value("ARG_OUT_OF_RANGE_START", RhspLibErrorCode::ARG_OUT_OF_RANGE_START)
        .value("ARG_OUT_OF_RANGE_END",   RhspLibErrorCode::ARG_OUT_OF_RANGE_END)
        .finalize();

    py::native_enum<SerialErrorCode>(m, "SerialErrorCode", "enum.IntEnum")
        .value("GENERAL_ERROR",       SerialErrorCode::GENERAL_ERROR)
        .value("UNABLE_TO_OPEN",      SerialErrorCode::UNABLE_TO_OPEN)
        .value("INVALID_ARGS",        SerialErrorCode::INVALID_ARGS)
        .value("CONFIGURATION_ERROR", SerialErrorCode::CONFIGURATION_ERROR)
        .value("IO_ERROR",            SerialErrorCode::IO_ERROR)
        .finalize();

    // ── Serial class ──────────────────────────────────────────────────────
    py::class_<PySerial>(m, "Serial")
        .def(py::init<>())
        .def("open",  &PySerial::open,
             py::arg("port"), py::arg("baudrate"), py::arg("databits"),
             py::arg("parity"), py::arg("stopbits"), py::arg("flow_control"))
        .def("close", &PySerial::close)
        .def("read",  &PySerial::read,  py::arg("num_bytes"))
        .def("write", &PySerial::write, py::arg("bytes"));

    // ── RevHub class ──────────────────────────────────────────────────────
    py::class_<PyRevHub>(m, "RevHub")
        .def(py::init<>())
        .def("open",  &PyRevHub::open,
             py::arg("serial"), py::arg("dest_address"))
        .def("is_opened",             &PyRevHub::is_opened)
        .def("close",                 &PyRevHub::close)
        .def("set_dest_address",      &PyRevHub::set_dest_address,      py::arg("addr"))
        .def("get_dest_address",      &PyRevHub::get_dest_address)
        .def("set_response_timeout_ms", &PyRevHub::set_response_timeout_ms, py::arg("ms"))
        .def("get_response_timeout_ms", &PyRevHub::get_response_timeout_ms)
        .def("send_write_command",    &PyRevHub::send_write_command,
             py::arg("packet_type_id"), py::arg("payload"))
        .def("send_read_command",     &PyRevHub::send_read_command,
             py::arg("packet_type_id"), py::arg("payload"))
        .def("get_module_status",     &PyRevHub::get_module_status,     py::arg("clear"))
        .def("send_keep_alive",       &PyRevHub::send_keep_alive)
        .def("send_fail_safe",        &PyRevHub::send_fail_safe)
        .def("set_new_module_address",&PyRevHub::set_new_module_address, py::arg("new_addr"))
        .def("query_interface",       &PyRevHub::query_interface,        py::arg("name"))
        .def("get_interface_packet_id", &PyRevHub::get_interface_packet_id,
             py::arg("name"), py::arg("function_number"))
        .def("set_debug_log_level",   &PyRevHub::set_debug_log_level,
             py::arg("group"), py::arg("level"))
        // LED
        .def("set_module_led_color",  &PyRevHub::set_module_led_color,
             py::arg("red"), py::arg("green"), py::arg("blue"))
        .def("get_module_led_color",  &PyRevHub::get_module_led_color)
        .def("set_module_led_pattern",&PyRevHub::set_module_led_pattern, py::arg("steps"))
        .def("get_module_led_pattern",&PyRevHub::get_module_led_pattern)
        // Device control
        .def("get_bulk_input_data",   &PyRevHub::get_bulk_input_data)
        .def("get_adc",               &PyRevHub::get_adc,
             py::arg("channel"), py::arg("raw_mode"))
        .def("phone_charge_control",  &PyRevHub::phone_charge_control,  py::arg("enable"))
        .def("phone_charge_query",    &PyRevHub::phone_charge_query)
        .def("inject_data_log_hint",  &PyRevHub::inject_data_log_hint,  py::arg("hint"))
        .def("read_version_string",   &PyRevHub::read_version_string)
        .def("read_version",          &PyRevHub::read_version)
        .def("ftdi_reset_control",    &PyRevHub::ftdi_reset_control,    py::arg("enable"))
        .def("ftdi_reset_query",      &PyRevHub::ftdi_reset_query)
        // Digital I/O
        .def("set_single_digital_output", &PyRevHub::set_single_digital_output,
             py::arg("pin"), py::arg("value"))
        .def("set_all_digital_outputs",   &PyRevHub::set_all_digital_outputs, py::arg("packed"))
        .def("set_digital_direction",     &PyRevHub::set_digital_direction,
             py::arg("pin"), py::arg("direction_output"))
        .def("get_digital_direction",     &PyRevHub::get_digital_direction,   py::arg("pin"))
        .def("get_single_digital_input",  &PyRevHub::get_single_digital_input, py::arg("pin"))
        .def("get_all_digital_inputs",    &PyRevHub::get_all_digital_inputs)
        // I2C
        .def("configure_i2c_channel",     &PyRevHub::configure_i2c_channel,
             py::arg("channel"), py::arg("speed_code"))
        .def("configure_i2c_query",       &PyRevHub::configure_i2c_query,     py::arg("channel"))
        .def("write_single_byte",         &PyRevHub::write_single_byte,
             py::arg("channel"), py::arg("addr"), py::arg("byte"))
        .def("write_multiple_bytes",      &PyRevHub::write_multiple_bytes,
             py::arg("channel"), py::arg("addr"), py::arg("bytes"))
        .def("write_status_query",        &PyRevHub::write_status_query,      py::arg("channel"))
        .def("read_single_byte",          &PyRevHub::read_single_byte,
             py::arg("channel"), py::arg("addr"))
        .def("read_multiple_bytes",       &PyRevHub::read_multiple_bytes,
             py::arg("channel"), py::arg("addr"), py::arg("n"))
        .def("write_read_multiple_bytes", &PyRevHub::write_read_multiple_bytes,
             py::arg("channel"), py::arg("addr"), py::arg("n"), py::arg("start_address"))
        .def("read_status_query",         &PyRevHub::read_status_query,       py::arg("channel"))
        // Motor
        .def("set_motor_channel_mode",    &PyRevHub::set_motor_channel_mode,
             py::arg("channel"), py::arg("mode"), py::arg("float_at_zero"))
        .def("get_motor_channel_mode",    &PyRevHub::get_motor_channel_mode,  py::arg("channel"))
        .def("set_motor_channel_enable",  &PyRevHub::set_motor_channel_enable,
             py::arg("channel"), py::arg("enable"))
        .def("get_motor_channel_enable",  &PyRevHub::get_motor_channel_enable, py::arg("channel"))
        .def("set_motor_channel_current_alert_level",
             &PyRevHub::set_motor_channel_current_alert_level,
             py::arg("channel"), py::arg("limit_ma"))
        .def("get_motor_channel_current_alert_level",
             &PyRevHub::get_motor_channel_current_alert_level, py::arg("channel"))
        .def("reset_encoder",             &PyRevHub::reset_encoder,           py::arg("channel"))
        .def("set_motor_constant_power",  &PyRevHub::set_motor_constant_power,
             py::arg("channel"), py::arg("power"))
        .def("get_motor_constant_power",  &PyRevHub::get_motor_constant_power, py::arg("channel"))
        .def("set_motor_target_velocity", &PyRevHub::set_motor_target_velocity,
             py::arg("channel"), py::arg("velocity_cps"))
        .def("get_motor_target_velocity", &PyRevHub::get_motor_target_velocity, py::arg("channel"))
        .def("set_motor_target_position", &PyRevHub::set_motor_target_position,
             py::arg("channel"), py::arg("position"), py::arg("tolerance"))
        .def("get_motor_target_position", &PyRevHub::get_motor_target_position, py::arg("channel"))
        .def("is_motor_at_target",        &PyRevHub::is_motor_at_target,      py::arg("channel"))
        .def("get_encoder_position",      &PyRevHub::get_encoder_position,    py::arg("channel"))
        .def("set_closed_loop_control_coefficients",
             &PyRevHub::set_closed_loop_control_coefficients,
             py::arg("channel"), py::arg("mode"), py::arg("params"))
        .def("get_closed_loop_control_coefficients",
             &PyRevHub::get_closed_loop_control_coefficients,
             py::arg("channel"), py::arg("mode"))
        // Servo
        .def("set_servo_configuration",   &PyRevHub::set_servo_configuration,
             py::arg("channel"), py::arg("frame_period"))
        .def("get_servo_configuration",   &PyRevHub::get_servo_configuration, py::arg("channel"))
        .def("set_servo_pulse_width",     &PyRevHub::set_servo_pulse_width,
             py::arg("channel"), py::arg("width"))
        .def("get_servo_pulse_width",     &PyRevHub::get_servo_pulse_width,   py::arg("channel"))
        .def("set_servo_enable",          &PyRevHub::set_servo_enable,
             py::arg("channel"), py::arg("enable"))
        .def("get_servo_enable",          &PyRevHub::get_servo_enable,        py::arg("channel"))
        // Static
        .def_static("discover_rev_hubs",  &PyRevHub::discover_rev_hubs,       py::arg("serial"));
}
